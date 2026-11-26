from services.supabase_client import supabase


# Test upload dummy file
if __name__ == "__main__":
    # Buat file dummy
    dummy_path = "dummy.txt"
    with open(dummy_path, "w") as f:
        f.write("Halo dari backend!")

    # Upload ke bucket 'ndvi-results'
    with open(dummy_path, "rb") as f:
        res = supabase.storage.from_("analysis-result").upload(dummy_path, f)

    print("Upload response:", res)