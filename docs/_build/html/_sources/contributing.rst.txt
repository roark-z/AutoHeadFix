Contributing
==========================



Editing Documentation
--------------------------------
Documentation can be found in the :code:`docs` folder. The documentations is built with `Sphinx <https://www.sphinx-doc.org/en/master/>`_, which can be installed through `apt, conda, or pip <https://www.sphinx-doc.org/en/master/usage/installation.html>`_

Minor changes can be included directly in the docstrings of the relevant :code:`.py` files; major changes can be made by modifying the :code:`.rst` files.  Run :code:`make clean; make html` to rebuild html files after making changes. Do not modify html files directly, as they will be overwritten.

Please make sure to update docs as soon as changes are finalised! Ensure docs and code are updated in a single commit to prevent mismatches and outdated documentation.
