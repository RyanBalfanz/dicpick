dump_production_database:
	python -m materiality.util.dump_production_database --app-name=dicpick

compilemessages:
	python manage.py compilemessages

isort:
	isort -rc main/ dicpick/

makemessages:
	python ../manage.py makemessages --all

nuke_db:
	python -m materiality.util.nuke_db
