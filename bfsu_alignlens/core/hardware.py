from __future__ import annotations

from typing import Dict, List


def torch_available() -> bool:
    try:
        import torch  # type: ignore
        return True
    except Exception:
        return False


def get_hardware_info() -> Dict:
    info = {
        'torch_installed': False,
        'torch_version': '',
        'torch_cuda_version': '',
        'cudnn_version': '',
        'cuda_available': False,
        'device_count': 0,
        'devices': [],
        'suggested_device': 'cpu',
        'diagnostic': '',
    }
    try:
        import torch  # type: ignore
        info['torch_installed'] = True
        info['torch_version'] = getattr(torch, '__version__', '')
        info['torch_cuda_version'] = str(getattr(torch.version, 'cuda', '') or '')
        try:
            info['cudnn_version'] = str(torch.backends.cudnn.version() or '')
        except Exception:
            info['cudnn_version'] = ''
        try:
            info['cuda_available'] = bool(torch.cuda.is_available())
        except Exception as exc:
            info['cuda_available'] = False
            info['diagnostic'] = f'torch.cuda.is_available() failed: {exc}'
        if info['cuda_available']:
            info['device_count'] = torch.cuda.device_count()
            for i in range(info['device_count']):
                props = torch.cuda.get_device_properties(i)
                info['devices'].append({
                    'index': i,
                    'name': torch.cuda.get_device_name(i),
                    'total_memory_gb': round(props.total_memory / 1024**3, 2),
                })
            info['suggested_device'] = 'cuda:0'
            info['diagnostic'] = 'CUDA is available.'
        else:
            if info['torch_cuda_version']:
                info['diagnostic'] = (
                    'Torch is installed with CUDA runtime support, but torch.cuda.is_available() is False. '
                    'Check the NVIDIA driver, Windows GPU driver visibility, and whether another Python environment is being used.'
                )
            else:
                info['diagnostic'] = (
                    'Torch is installed, but this appears to be a CPU-only PyTorch build. '
                    'The bundled requirements.txt now requests the CUDA-enabled PyTorch wheel by default; '
                    'rerun pip install -r requirements.txt in the same environment, or choose a different cuXXX wheel if your NVIDIA driver requires it.'
                )
    except Exception as exc:
        info['error'] = str(exc)
        info['diagnostic'] = (
            'PyTorch is not importable in the active Python environment. '
            'Install torch in the same virtual environment used to run AlignLens.'
        )
    return info


def format_hardware_message(info: Dict) -> str:
    if info.get('cuda_available'):
        devs = ', '.join(
            f"CUDA:{d['index']} {d['name']} ({d['total_memory_gb']}GB)"
            for d in info.get('devices', [])
        )
        return (
            f"CUDA available: {devs}. "
            f"Torch {info.get('torch_version') or 'unknown'}, CUDA runtime {info.get('torch_cuda_version') or 'unknown'}."
        )
    if info.get('torch_installed'):
        return (
            "CUDA is not active in this Python environment; CPU mode will be used. "
            f"Torch {info.get('torch_version') or 'unknown'}, "
            f"CUDA runtime {info.get('torch_cuda_version') or 'not included'}. "
            f"{info.get('diagnostic') or ''}"
        )
    return (
        "PyTorch is not importable in this Python environment; CPU mode will be used. "
        f"{info.get('diagnostic') or info.get('error') or ''}"
    )


def available_device_options() -> List[str]:
    info = get_hardware_info()
    opts = ['auto', 'cpu']
    if info.get('cuda_available'):
        opts.extend([f'cuda:{x["index"]}' for x in info.get('devices', [])])
    return opts


def resolve_device(device: str) -> str:
    info = get_hardware_info()
    if device == 'auto':
        return info.get('suggested_device', 'cpu')
    if device.startswith('cuda') and not info.get('cuda_available'):
        return 'cpu'
    return device or 'cpu'


def cpu_light_settings() -> Dict:
    return {
        'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'alignment_mode': 'minilm',
        'max_window': 2,
        'batch_size': 16,
        'use_fused_similarity': False,
        'residual_matching': False,
        'paragraph_constraint': True,
        'device': 'cpu',
    }
