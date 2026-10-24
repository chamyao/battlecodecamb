# rev: 16aa3b56ec2ffb0c2b52b08a01b08eedd25dc21b
# genome/simspeed: bit-exactness of the sped-up simulator vs the original (genome/v0 5ed2e97), 10 seeds
# (3,440 games per binary: genome vs .pol, .pol vs .pol, genome vs starter, starter vs .pol, --bot-seeds, genome vs genome)
git cat-file -e 5ed2e97^{commit} 2>/dev/null || git fetch -q --unshallow origin 2>/dev/null || git fetch -q origin genome/v0
SEEDS="1 2 3 4 5 6 7 8 9 10" genome/tools/exact_suite.sh 5ed2e97 $OUT/suite > $OUT/result.txt 2>&1
tail -3 $OUT/result.txt
rm -rf $OUT/suite/base $OUT/suite/so-base $OUT/suite/so-new
