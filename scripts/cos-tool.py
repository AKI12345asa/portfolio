"""腾讯云 COS 视频托管工具：上传 → 私有存储 → 生成带签名的临时链接。

为什么需要它：
  存储桶设成「私有读写」后，文件没有公开地址，只能靠带签名的 URL 访问。
  签名里含有效期，过期即失效，这样"只给链接才能看"才是真的可控。

准备（只需一次）：
  1. 复制 .env.example 为 .env，填入 SecretId / SecretKey / 存储桶 / 地域
  2. python scripts/cos-tool.py check         # 验证配置和连通性

常用命令：
  python scripts/cos-tool.py ls                              # 看看桶里有什么
  python scripts/cos-tool.py upload 文件.mp4 --key works/a.mp4
  python scripts/cos-tool.py sign --key works/a.mp4 --days 7
  python scripts/cos-tool.py verify --url "https://..."       # 验证链接真能播
  python scripts/cos-tool.py publish 文件.mp4 --key works/a.mp4 --label "完整流程演示 · 07:56"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Windows 控制台默认 GBK，中文和长 URL 会乱码，强制切 UTF-8
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# COS SDK 装在项目的 .tools/pylibs 里，不污染系统 Python 环境
_LIBS = PROJECT_ROOT / '.tools' / 'pylibs'
if _LIBS.is_dir() and str(_LIBS) not in sys.path:
    sys.path.insert(0, str(_LIBS))

ENV_FILE = PROJECT_ROOT / '.env'
REQUIRED = ('COS_SECRET_ID', 'COS_SECRET_KEY', 'COS_REGION', 'COS_BUCKET')

MIME = {
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.m4v': 'video/x-m4v',
    '.mp3': 'audio/mpeg',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.vtt': 'text/vtt',
}


def load_env():
    """从 .env 读配置，也允许直接用系统环境变量覆盖。"""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print('缺少配置：' + ', '.join(missing), file=sys.stderr)
        print(f'请复制 {ENV_FILE.with_suffix(".example")} 为 {ENV_FILE} 并填写。', file=sys.stderr)
        sys.exit(2)

    return {
        'SecretId': os.environ['COS_SECRET_ID'],
        'SecretKey': os.environ['COS_SECRET_KEY'],
        'Region': os.environ['COS_REGION'],
        'Bucket': os.environ['COS_BUCKET'],
    }


def client(cfg):
    from qcloud_cos import CosConfig, CosS3Client
    conf = CosConfig(
        Region=cfg['Region'],
        SecretId=cfg['SecretId'],
        SecretKey=cfg['SecretKey'],
        Scheme='https',
    )
    return CosS3Client(conf)


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.1f} {unit}' if unit != 'B' else f'{int(n)} B'
        n /= 1024


def cmd_check(args):
    cfg = load_env()
    c = client(cfg)
    resp = c.list_objects(Bucket=cfg['Bucket'], MaxKeys=5)
    keys = [o['Key'] for o in resp.get('Contents', [])]
    print(f"✓ 配置正常")
    print(f"  存储桶 : {cfg['Bucket']}")
    print(f"  地域   : {cfg['Region']}")
    print(f"  对象数 : {len(keys)}（以下最多列 5 个）")
    for k in keys:
        print(f'    - {k}')

    # 顺手确认桶是不是私有：匿名 GET 应当被拒绝
    from urllib.parse import quote
    import urllib.request
    import urllib.error
    host = f"https://{cfg['Bucket']}.cos.{cfg['Region']}.myqcloud.com/"
    try:
        urllib.request.urlopen(host, timeout=8)
        print('  ⚠ 警告：匿名访问似乎成功了，桶可能设成了「公有读」')
        print('    请到控制台把访问权限改成「私有读写」')
    except urllib.error.HTTPError as e:
        if e.code in (403, 401):
            print('  ✓ 私有性检查通过（匿名访问被拒绝 403）')
        else:
            print(f'  匿名访问返回 HTTP {e.code}，请自行确认桶权限')
    except Exception as e:
        print(f'  匿名访问检查跳过：{e}')


def cmd_ls(args):
    cfg = load_env()
    c = client(cfg)
    prefix = args.prefix or ''
    marker = ''
    total = 0
    while True:
        resp = c.list_objects(Bucket=cfg['Bucket'], Prefix=prefix, Marker=marker, MaxKeys=1000)
        contents = resp.get('Contents', [])
        for o in contents:
            print(f"{human(int(o['Size'])):>10}  {o['Key']}")
            total += 1
        if resp.get('IsTruncated') == 'true':
            marker = contents[-1]['Key']
        else:
            break
    print(f'共 {total} 个对象')


def cmd_upload(args, cfg=None):
    cfg = cfg or load_env()
    c = client(cfg)
    path = Path(args.file)
    if not path.is_file():
        print(f'找不到文件：{path}', file=sys.stderr)
        return None

    key = args.key or path.name
    size = path.stat().st_size
    ctype = MIME.get(path.suffix.lower(), 'application/octet-stream')

    print(f'上传 {path.name} ({human(size)}) → {key}  [{ctype}]')
    if size > 20 * 1024 * 1024:
        # 大文件走分块上传，断了可以重试，比单次 PUT 稳
        c.upload_file(
            Bucket=cfg['Bucket'],
            Key=key,
            LocalFilePath=str(path),
            PartSize=8,
            MAXThread=4,
            EnableMD5=False,
            ContentType=ctype,
        )
    else:
        with path.open('rb') as f:
            c.put_object(
                Bucket=cfg['Bucket'],
                Body=f,
                Key=key,
                ContentType=ctype,
                EnableMD5=False,
            )
    print('✓ 上传完成')
    print(f'  本地原文件保留在 {path}')
    return key


def cmd_sign(args):
    cfg = load_env()
    c = client(cfg)
    seconds = max(60, int(args.days * 86400))
    url = c.get_presigned_url(
        Bucket=cfg['Bucket'],
        Key=args.key,
        Method='GET',
        Expired=seconds,
        SignHost=True,
    )
    if args.json:
        print(json.dumps({'key': args.key, 'url': url, 'days': args.days}, ensure_ascii=False, indent=2))
    else:
        days = int(args.days) if float(args.days).is_integer() else args.days
        print(f'# {args.key}  有效期 {days} 天')
        print(url)
    return url


def cmd_verify(args):
    import urllib.request
    import urllib.error

    # 优先用 --key 现签：签名 URL 里带 &，经 cmd 传参会把 URL 截断
    if getattr(args, 'key', None):
        cfg = load_env()
        c = client(cfg)
        url = c.get_presigned_url(
            Bucket=cfg['Bucket'],
            Key=args.key,
            Method='GET',
            Expired=int(getattr(args, 'days', 7) * 86400),
            SignHost=True,
        )
    elif getattr(args, 'url', None):
        url = args.url
    else:
        print('请用 --key 或 --url 指定要验证的目标', file=sys.stderr)
        sys.exit(2)

    req = urllib.request.Request(url, method='GET', headers={'Range': 'bytes=0-1023'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
            print(f'✓ 链接有效  HTTP {r.status}')
            print(f'  Content-Type : {r.headers.get("Content-Type")}')
            print(f'  Content-Range: {r.headers.get("Content-Range")}')
            print(f'  实际读到     : {human(len(data))}')
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode('utf-8', 'replace')
        print(f'✗ HTTP {e.code}', file=sys.stderr)
        print(f'  {body}', file=sys.stderr)
        if e.code in (403, 400):
            print('  常见原因：签名过期 / SecretKey 不对 / 系统时间偏差过大', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'✗ 请求失败：{e}', file=sys.stderr)
        sys.exit(1)


def cmd_publish(args):
    cfg = load_env()
    key = cmd_upload(args, cfg)
    if not key:
        return
    url = cmd_sign(argparse.Namespace(key=key, days=args.days, json=False))
    label = args.label or Path(args.file).stem
    print()
    print('把下面这段贴进作品的 frontmatter：')
    print('-' * 60)
    # 签名 URL 里有 & 和 %，YAML 里必须加引号，否则解析出错
    print('demo:')
    print('  type: local')
    print(f"  src: '{url}'")
    print(f"  label: '{label}'")
    print('-' * 60)
    print('注意：链接有有效期，到期后重新执行 sign 或 publish 即可。')


def main():
    ap = argparse.ArgumentParser(description='腾讯云 COS 视频托管工具')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('check', help='验证配置、连通性和桶的私有性')
    p.set_defaults(func=cmd_check)

    p = sub.add_parser('ls', help='列出桶内对象')
    p.add_argument('--prefix', default='')
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser('upload', help='上传文件')
    p.add_argument('file')
    p.add_argument('--key', help='对象键，默认用文件名')
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser('sign', help='生成签名链接')
    p.add_argument('--key', required=True)
    p.add_argument('--days', type=float, default=7, help='有效期天数，默认 7')
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_sign)

    p = sub.add_parser('verify', help='验证签名链接是否可用（推荐用 --key）')
    p.add_argument('--key', help='对象键，推荐这样用（避免 shell 把 URL 里的 & 吃掉）')
    p.add_argument('--url', help='完整签名 URL，注意在 shell 里要加引号')
    p.add_argument('--days', type=float, default=7, help='配合 --key 时的有效期，默认 7')
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser('publish', help='上传 + 签名 + 输出 frontmatter 片段')
    p.add_argument('file')
    p.add_argument('--key')
    p.add_argument('--days', type=float, default=7)
    p.add_argument('--label')
    p.set_defaults(func=cmd_publish)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
