#!/bin/bash
git fetch -t
last=`git describe --abbrev=0 --tags`
if [[ $? -eq 0 ]];
then
    echo $last
    ref=`git show-ref -s $last`
    echo $ref
    git --no-pager log $ref..$GITHUB_SHA --oneline
else
    echo "No previous tags found"
    git --no-pager log $GITHUB_SHA --oneline
fi
