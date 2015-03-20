#!/bin/bash


set -e
# Get the list of tests to run from command line or take all tests from the
# default path
if [[ $# -ne 0 ]] ; then
	TESTS=$@
else
	TESTS=(`ls tests.d/*`)
fi

function finish {
	rm -rf -- "$TMP"
}
trap finish EXIT


export AUTO_TEST='yes'

declare -A TEMPLATES
[ -f /etc/debian_version ] && TEMPLATES[DEBIAN_VERSION]="$(cat /etc/debian_version)"
[ -f /etc/debian_version ] && TEMPLATES[DEBIAN_VERSION_ENC]="${TEMPLATES[DEBIAN_VERSION]/\//%2F}"

# Run tests one by one
for A in ${TESTS[*]} ; do
	echo $A

	# Create temporary directory for storing test's outputs
	export TMP=$(mktemp -d)

	EXPECTED_STDOUT=$TMP/expected_stdout
	EXPECTED_STDERR=$TMP/expected_stderr
	REAL_STDOUT=$TMP/real_stdout
	REAL_STDERR=$TMP/real_stderr
	TEMPLATES[CWD]=$TMP

	# Extract expected output and real output (by running the test scenario)
	sed -n -e 's/^#o \?\(.*\)$/\1/p' -e 's/^\(Scenario .*\)$/\n\n\1\n\n/p' -e 's/^\(Testcase .*\)$/\n\1\n/p' -- "$A" | sed "s|\$TMP|$TMP|g" >"$EXPECTED_STDOUT"
	sed -n -e 's/^#e \?\(.*\)$/\1/p' -e 's/^\(Scenario .*\)$/\n\n\1\n\n/p' -e 's/^\(Testcase .*\)$/\n\1\n/p' -- "$A" | sed "s|\$TMP|$TMP|g" >"$EXPECTED_STDERR"

	for key in "${!TEMPLATES[@]}" ; do
		sed -i "s!%$key%!${TEMPLATES[$key]}!g" $EXPECTED_STDERR
		sed -i "s!%$key%!${TEMPLATES[$key]}!g" $EXPECTED_STDOUT
	done


	bash $A >"$REAL_STDOUT" 2>"$REAL_STDERR" || true

	# Display differences
	diff -u -- "$EXPECTED_STDERR" "$REAL_STDERR"
	diff -u -- "$EXPECTED_STDOUT" "$REAL_STDOUT"

	rm -rf -- "$TMP"
done

echo 'SUCCESS'

