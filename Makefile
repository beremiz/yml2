YML_PATH  =
DEBVER   := 1
PYTHON   := python3
PKGVER    = $(shell awk '/^version/ {print $$3}' setup.cfg)
TWINE    := $(PYTHON) -m twine
TWINEREP := pypi
YML2C     = $(PYTHON) yml2c

all: homepage

homepage: index.html features.html yslt.html toolchain.html programming.html hello.html

update: homepage format.css COPYING.txt
	rsync -avC *.html *.yml2 format.css *.yhtml2 COPYING.txt samples dragon:fdik.org/yml2/

update-all: update yml2c yml2.py pyPEG.py backend.py yml2proc
	if test -z $(VERSION) ; then echo VERSION not set ; exit 1 ; fi
	rsync -avC *.py yml2 yml2c Makefile yml2proc xml2yml.ysl2 standardlib.ysl2 samples dragon:fdik.org/yml2/
	ssh dragon bash -c "cd ; cd fdik.org/; tar cvjf yml-$(VERSION).tar.bz2 yml2/{*.py,*.yml2,*.yhtml2,format.css,COPYING.txt,yml2,yml2c,Makefile,yml2proc,xml2yml.ysl2,standardlib.ysl2,samples} ; rm yml2.tar.bz2 ; ln -s yml-$(VERSION).tar.bz2 yml2.tar.bz2"

%.html: %.en.yhtml2 heading.en.yhtml2 homepage.en.yhtml2
	$(YML2C) $< -o $@

.PHONY: deb
deb:  YML2_$(PKGVER).orig.tar.gz python-yml2_$(PKGVER)-$(DEBVER)_all.deb

YML2_$(PKGVER).orig.tar.gz:
	python setup.py sdist
	mv -f dist/YML2-$(PKGVER).tar.gz YML2_$(PKGVER).orig.tar.gz

python-yml2_$(PKGVER)-$(DEBVER)_all.deb:
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb
	mv -f deb_dist/python-yml2_$(PKGVER)-$(DEBVER)_all.deb .

clean:
	rm -f *.html *.pyc *.pyo */*.pyc */*.pyo
	rm -rf *.egg-info
	rm -f YML2_$(PKGVER).orig.tar.gz
	rm -f python-yml2_$(PKGVER)-$(DEBVER)_all.deb
	rm -f dist/YML2-$(PKGVER).tar.gz

sdist-pypi: dist/YML2-$(PKGVER).tar.gz
	$(TWINE) check $<

upload-pypi: sdist-pypi
	$(TWINE) upload --repository "$(TWINEREP)" $<

.PHONY: dist/YML2-$(PKGVER).tar.gz
dist/YML2-$(PKGVER).tar.gz:
	$(PYTHON) setup.py sdist

install:
	pip install -e .

