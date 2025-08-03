from setuptools import setup, find_packages

setup(
    name="web-eval-agent",
    version="2.0.0",
    description="AI-powered web testing CLI tool using GEMINI API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Web Eval Agent Team",
    author_email="team@webevalagent.com",
    url="https://github.com/Zeeeepa/web-eval-agent",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "browser-use>=0.1.40",
        "langchain-google-genai",
        "langchain-core<0.4.0",
        "google-generativeai<0.9.0",
        "playwright",
        "pydantic<3",
        "PyYAML",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
        ]
    },
    entry_points={
        "console_scripts": [
            "web-eval=web_eval_agent.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    keywords="web testing automation ai browser evaluation cli",
    project_urls={
        "Bug Reports": "https://github.com/Zeeeepa/web-eval-agent/issues",
        "Source": "https://github.com/Zeeeepa/web-eval-agent",
        "Documentation": "https://github.com/Zeeeepa/web-eval-agent#readme",
    },
)
