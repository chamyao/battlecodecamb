# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-6 (Arena A lead; Cham): arenaZ-1 with ONE change: funsearch.catalog GAME's "Observations from today's top-12
# ladder games" block (13 lines, through "- Builds: ... Bruiser (Power Strength for Vesper Vale).") left out of the operator
# system prompt (genome/search patches/no-ladder-obs.patch, acked by the Arena A lead 00:30). Everything else as arenaZ-1:
# 7e40b6f, runtime 648bafd, starter seed and only fixed anchor, champions every 50, $3, same RNG as arenaZ-1. Panel: arena service.
cp genome/examples/starter.genome $OUT/starter.genome
git apply <<'PATCH' || exit 1
--- a/genome/search/prompts.py
+++ b/genome/search/prompts.py
@@ -7,7 +7,10 @@
 
 LANGUAGE = (Path(__file__).resolve().parent.parent / "LANGUAGE.md").read_text()
 
-FACTS = GAME.replace("Every block a bot runs costs fuel", "Every operation and engine call a bot runs costs fuel") + """\
+# arenaZ-6: the funsearch.catalog "Observations from today's top-12 ladder games" block is left out of the prompt
+_OBS = GAME.index("Observations from today's top-12 ladder games")
+_GAME = GAME[:_OBS] + GAME[GAME.index("Bruiser (Power Strength for Vesper Vale).\n", _OBS) + len("Bruiser (Power Strength for Vesper Vale).\n"):]
+FACTS = _GAME.replace("Every block a bot runs costs fuel", "Every operation and engine call a bot runs costs fuel") + """\
 In a genome, compiled gene code is cheap (a few fuel per operation); engine calls (distance fields
 via field(), vision queries such as enemies()/camps()) cost more. A turn over budget is suspended.
 """
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -c "from genome.search import prompts; assert 'Observations from today' not in prompts.SYSTEM_BASE; print('ladder block removed')" || exit 1
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 3 --threads $THREADS --fixed-anchors --gate-every 100000000
