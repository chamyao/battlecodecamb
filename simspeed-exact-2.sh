# rev: 16d4909f2b2ae60679ed6a6da1ff6fe6a95af7ac
# genome/simspeed merged with genome/v0: bit-exactness vs genome/v0 212a505 (incl. deploy/v0 7ea42c7 interp), 10 seeds
# (3,440 games per binary: genome vs .pol, .pol vs .pol, genome vs starter, starter vs .pol, --bot-seeds, genome vs genome)
git cat-file -e 212a505^{commit} 2>/dev/null || git fetch -q --unshallow origin 2>/dev/null || git fetch -q origin genome/v0
SEEDS="1 2 3 4 5 6 7 8 9 10" genome/tools/exact_suite.sh 212a505 $OUT/suite > $OUT/result.txt 2>&1
tail -3 $OUT/result.txt
