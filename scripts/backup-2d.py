"""Preserve the approved 2D pilot before the offline 3D renderer replaces media.

Creation is idempotent: an existing snapshot is verified, never overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / 'backups' / '2d-v2-20261106'
MANIFEST = BACKUP / 'backup-manifest.json'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    for item in manifest['files']:
        target = BACKUP / item['path']
        if not target.is_file() or sha256(target) != item['sha256']:
            raise RuntimeError(f"Backup missing or changed: {item['path']}")
    print(f"2D backup verified: {len(manifest['files'])} files, {manifest['bytes'] / 1024 / 1024:.2f} MiB: {BACKUP}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Only verify the existing immutable snapshot.')
    args = parser.parse_args()
    if MANIFEST.exists():
        verify()
        return
    if args.verify:
        raise FileNotFoundError(f'No snapshot exists at {MANIFEST}')
    if BACKUP.exists() and any(BACKUP.iterdir()):
        raise RuntimeError('Snapshot directory exists without a manifest; refusing to overwrite it.')
    sources = [*sorted((ROOT / 'dist' / 'assets' / 'animations').glob('*')),
               ROOT / 'dist' / 'data.js', ROOT / 'scripts' / 'assemble-animations.py',
               ROOT / 'docs' / 'animation-build.json', ROOT / 'docs' / 'prompts' / 'animation-prompts.json',
               ROOT / 'docs' / 'prompts' / 'animation-prompts-v2.json']
    for directory in ['generated-frames', 'generated-frames-v2']:
        sources.extend(sorted((ROOT / 'docs' / directory).glob('*.png')))
    records = []
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(source)
        relative = source.relative_to(ROOT).as_posix()
        destination = BACKUP / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        records.append({'path': relative, 'bytes': source.stat().st_size, 'sha256': sha256(source)})
    manifest = {'description': 'Approved colored 2D v2 pilot: 16-frame GIFs, posters, all v1/v2 generated source sheets, prompts and data.',
                'createdForClientDate': '2026-11-06', 'files': records,
                'bytes': sum(item['bytes'] for item in records)}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (BACKUP / 'RESTORE.md').write_text('''# Backup do piloto 2D\n\nEste snapshot contém os GIFs coloridos de 16 quadros, os pôsteres, as folhas de quadros das duas versões, os prompts e os arquivos necessários para reconstruir a mídia. O site não baixa estes arquivos de backup.\n\nVerificação de integridade na raiz do projeto:\n\n```sh\npython scripts/backup-2d.py --verify\n```\n\nPara retornar ao piloto 2D, copie o conteúdo de `dist/assets/animations/` deste snapshot para a pasta de mesmo nome na raiz do projeto e restaure `dist/data.js` deste snapshot. Depois execute `npm run build` e `npm run check`. A interface aceita os arquivos 2D originais; os fontes 3D podem permanecer separados.\n\nPara reconstruir as imagens da versão 2D, também há cópias do script `scripts/assemble-animations.py`, dos fontes em `docs/generated-frames-v2/` e dos prompts. Restaure esses arquivos somente se desejar editar a produção 2D novamente.\n\n`backup-manifest.json` registra o SHA-256 e o tamanho de cada arquivo preservado. Uma execução normal de `backup-2d.py` verifica este snapshot se ele já existe, sem substituí-lo.\n''', encoding='utf-8')
    verify()


if __name__ == '__main__':
    main()
