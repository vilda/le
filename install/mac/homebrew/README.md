Homebrew packaging
==================

This is here as a convenience for the test/release process. It is possible
install the agent via...

    cd le/install/mac/homebrew
    brew install --verbose --debug logentries.rb

To update the package to a know version the url and sha256 fields need
to be updated accordingly

It is also possible to install the latest commit from the master branch
by doing...

    cd le/install/mac/homebrew
    brew install --HEAD --verbose --debug logentries.rb
