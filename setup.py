from setuptools import setup, find_packages

setup(
    name="iagent-pay",
    version="1.0.1",
    description="The First Payment SDK for Autonomous AI Agents.",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    author="AgentPay Inc.",
    author_email="hello@agentpay.ai",
    url="https://github.com/agent-pay/sdk",
    packages=find_packages(),
    # If we keep flat structure, we might need py_modules, but we will move to a package structure.
    # py_modules=["iagent_pay", "wallet_manager", "config", "pricing"], 
    install_requires=[
        "web3>=6.0.0",
        "eth-account>=0.8.0",
        "python-dotenv>=1.0.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires='>=3.7',
)
