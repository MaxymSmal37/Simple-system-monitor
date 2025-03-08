# Project Setup
>**Note:** Tested on macOS

Create a Virtual Environment

```bash 
python -m venv myenv
```

### Activate the Virtual Environment

#### Linux/macOS:

```bash 
source myenv/bin/activate
```

#### Windows:

```bash 
myenv\Scripts\activate
```

### Install Required Packages

```bash 
uv pip install psutil rich
uv pip install tinydb

```

### Run the Python Script

```bash 
python SystemInfo.py
```

### For deactivate the Virtual Environment

```bash 
deactivate
``` 
