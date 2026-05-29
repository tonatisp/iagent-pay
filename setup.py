from setuptools import setup, find_packages

setup(
    name="iagent-pay",
    version="6.0.0",
    description="Universal AI Agent Banking Layer: 25 modules, 6 chains, x402, Safety Kernel, MCP, CrewAI, LangChain, Fiat Bridge",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="iAgent Team",
    author_email="hello@agentpay.ai",
    url="https://github.com/tonatisp/iagent-pay",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'iagent-pay=iagent_pay.cli:main',
        ],
    },
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.8.0",
        "python-dotenv>=1.0.0",
        "solana>=0.30.0",
        "solders>=0.18.0",
        "requests>=2.28.0",
        "httpx>=0.24.0",
    ],
    extras_require={
        "fastapi":   ["fastapi>=0.100.0", "starlette>=0.27.0", "uvicorn>=0.22.0"],
        "flask":     ["flask>=2.3.0"],
        "crewai":    ["crewai>=0.1.0"],
        "langchain": ["langchain>=0.1.0"],
        "fiat":      ["stripe>=5.0.0"],
        "all": [
            "fastapi>=0.100.0", "starlette>=0.27.0", "uvicorn>=0.22.0",
            "flask>=2.3.0", "httpx>=0.24.0", "stripe>=5.0.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires='>=3.9',
    keywords="ai agents payments x402 usdc solana xrp ethereum polygon arbitrum bnb langchain crewai mcp blockchain fiat stripe webhooks safety-kernel reputation multi-chain autonomous",
)
