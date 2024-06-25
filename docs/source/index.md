# WML - World Modeling Language

**World Modeling Language (WML)** is a programming language designed for modeling real-world systems with ease.
It's meant to facilitate AI research and introduce deterministic instructions into AI model.

This is the official documentation for WML. It is a work in progress and will be updated regularly.

```{warning}
WML is in **Alpha stage**, things may change rapidly. It is not recommended for production use.
```

## Getting Started

### Prerequisites

- Ensure you have Python installed. WML is developed and tested with Python 3.11. Other versions may work, but are not
officially supported (yet).

### Installation

1. Clone the repository:
```{code-block} bash
---
linenos: true
emphasize-lines: 1, 2
---
git clone https://github.com/kennylajara/WML.git
cd WML
```

2. Install the required dependencies:
```{code-block} bash
---
linenos: true
emphasize-lines: 1
---
pip install -r requirements.txt
```

## Placeholder

You can autogenerate documentation for your functions using the `sphinx_example` decorator. 

```{eval-rst}
.. autofunction:: wml.sphinx_example
```

Also, you can reference documented functions using the `:func:` role, for example: {py:func}`wml.sphinx_example`.
