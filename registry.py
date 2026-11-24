from web.adapters import (
    titrasyon_adapter,
    bradford_adapter,
    kromatografi_adapter,
    aspirin_adapter,
    coumarin_adapter,
    bakir_kompleks_adapter,
    egdma_hidrojel_adapter,
    isi_makinesi_adapter,
    elementel_analiz_adapter,
    impedimetri_adapter,
)

ADAPTERS = {
    "titrasyon": titrasyon_adapter,
    "bradford": bradford_adapter,
    "kromatografi": kromatografi_adapter,
    "aspirin": aspirin_adapter,
    "coumarin": coumarin_adapter,
    "bakir_kompleks": bakir_kompleks_adapter,
    "egdma_hidrojel": egdma_hidrojel_adapter,
    "isi_makinesi": isi_makinesi_adapter,
    "elementel_analiz": elementel_analiz_adapter,
    "impedimetri": impedimetri_adapter,
}

EXPERIMENTS = {k: mod.META for k, mod in ADAPTERS.items()}


def run_experiment_adapter(exp_id: str, params: dict) -> dict:
    if exp_id not in ADAPTERS:
        raise ValueError(f"Bilinmeyen deney: {exp_id}")
    return ADAPTERS[exp_id].run(params)
