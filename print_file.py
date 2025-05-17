from pathlib import Path


def write_swc(directory, file_name, lines, comment="", tmp=False):
    """Write an edited SWC file to *directory* and return its path."""
    # Creates downloads/files/ if needed and returns the written path
    dir_path = Path(directory) if tmp else Path(directory) / "downloads" / "files"
    dir_path.mkdir(parents=True, exist_ok=True)
    suffix = "_new_tmp.swc" if tmp else "_new.swc"
    out_path = dir_path / (file_name.replace(".swc", "") + suffix)

    with out_path.open("w", encoding="utf-8") as f:
        if comment:
            f.write(comment + "\n")
        f.write("\n".join(lines) + "\n")
    return out_path
