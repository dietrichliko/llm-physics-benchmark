import subprocess
import tomllib

MODEL_LISTS_PATH = "src/llm_physics_benchmark/model_lists.toml"

# Read model lists from TOML
with open(MODEL_LISTS_PATH, "rb") as f:
    config = tomllib.load(f)

models = set()
for tier in config.get("tiers", {}):
    models.update(config["tiers"][tier].get("models", []))


# Download each model (example: using 'ollama' CLI)
def download_model(model_name):
    print(f"Downloading model: {model_name}")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
    except Exception as e:
        print(f"Failed to download {model_name}: {e}")


if __name__ == "__main__":
    for model in models:
        download_model(model)
