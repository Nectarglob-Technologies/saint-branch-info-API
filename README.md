#python -m pip install --upgrade pip setuptools wheel
#pip install onnxruntime
#pip install insightface --prefer-binary
#need to install visual C++

"""
#Registry name should be lower case saintbranchinforeg
az acr create --resource-group rg-public-apps --name SaintBranchInfoReg --sku Basic --admin-enabled true

#before running below az acr build make sure saint-branch-api is selected and dockerfile exist in it
#dot is important. It means it will take source location as saint-branch-api folder 
az acr build --registry SaintBranchInfoReg --image face-app:v1 .

# Create the app and enable public ingress
# Replace <ENVIRONMENT_NAME> with something like 'saint-env'
az containerapp create \
  --name saint-branch-kp-api \
  --resource-group rg-public-apps \
  --environment saint-data-env \
  --image saintbranchinforeg.azurecr.io/face-app:latest \
  --registry-server saintbranchinforeg.azurecr.io \
  --ingress external \
  --target-port 8000 \
  --cpu 1.0 --memory 2.0Gi \
  --min-replicas 0 --max-replicas 1

# link to github
  az containerapp github-action add \
  --name saint-branch-kp-api \
  --resource-group rg-public-apps \
  --repo-url "




error: Microsoft Visual C++ 14.0 is required. Get it with “Build Tools for Visual Studio”


✅ What Visual C++ Build Tools to install

You should install:

🟦 Microsoft Visual C++ Build Tools
Or the full Visual Studio Community Edition, selecting these workloads:

C++ build tools

Windows 10/11 SDK

MSVC v14.x (latest)

📥 How to install
Option A — Visual Studio Build Tools (recommended for Python)

Go to:
https://learn.microsoft.com/visualstudio/releases/2022/build-tools

Download Build Tools for Visual Studio 2022.

In the installer, select:

📦 C++ build tools

✓ “MSVC v143” (or newest)

✓ “Windows 10 SDK” (or Windows 11 SDK if available)

Click Install and wait until done.

Option B — Full Visual Studio Community

If you already have (or prefer) full Visual Studio:

Install Visual Studio Community

In workloads, check:

Desktop development with C++

Windows SDK

Install.

"""

