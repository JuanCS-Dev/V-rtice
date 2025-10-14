"""
Ethical Frameworks Engine.

Implementa 4 frameworks éticos fundamentais para avaliação de action plans:
- Kantian Deontology: Categorical Imperative e respeito incondicional
- Utilitarian Calculus: Maximização de bem-estar agregado (Bentham/Mill)
- Virtue Ethics: Ética das virtudes aristotélica (Golden Mean)
- Principialism: 4 princípios de bioética (Beauchamp & Childress)

Lei Governante: Constituição Vértice v2.6
"""

from motor_integridade_processual.frameworks.base import (
    EthicalFramework,
    AbstractEthicalFramework
)
from motor_integridade_processual.frameworks.kantian import KantianDeontology
from motor_integridade_processual.frameworks.utilitarian import UtilitarianCalculus
from motor_integridade_processual.frameworks.virtue import VirtueEthics
from motor_integridade_processual.frameworks.principialism import Principialism


__all__ = [
    "EthicalFramework",
    "AbstractEthicalFramework",
    "KantianDeontology",
    "UtilitarianCalculus",
    "VirtueEthics",
    "Principialism",
]
