"""Read a cambc .repl26a bundle: list members and extract '@@' oracle lines from stdout."""
import sys, zipfile, re

def oracle_lines(path, team):
    z = zipfile.ZipFile(path)
    data = z.read(f"team-{team}.stdout")
    # stdout is interleaved with binary timeline markers; oracle lines are plain text after '@@'.
    for m in re.finditer(rb"@@([^\n]*)\n", data):
        yield m.group(1).decode("latin-1")

if __name__ == "__main__":
    path, team = sys.argv[1], sys.argv[2]
    for line in oracle_lines(path, team):
        print(line)
