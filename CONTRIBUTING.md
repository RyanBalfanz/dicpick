
Developing DICPick
==================

Working on DICPick requires experience with Python/Django. Familiarity with Postgresql, JQuery and CSS is recommended.


Setting Up a Dev Environment
----------------------------

* From the repo root run `./bootstrap.sh`.  You should only need to do this once for all time (per repo clone).
  This downloads a third-party helper library (`materiality.commons`, actually written by the author of DICPick
  for use on multiple projects) into `.bootstrap`.  That library contains code to set up and maintain 
  services built on Django+Postgres.

* Run `./setup_dev.sh`.  This will perform several steps:

    - Creates a Python virtualenv and install all needed third-party libraries into it.  Note that these include 
      `materiality.commons`, as it needs to be available to the virtualenv post-bootstrapping.  The copy in `.bootstrap`
      is no longer needed.
    - Asks you for various local settings, such as the Django SECRET_KEY, the Postgres database account password etc.
      These get written into `main/settings_local.py`, which is gitignored and not checked in to the repo.
      
      **Do not use the production values of these settings**.  These are intended to be different in each dev workspace,
      and in each production installation.  The first time you run the setup script you won't have values for these,
      so select 'N' to allow the script to generate them.
    - Sets up a local Postgres DB.
    - Runs the initial Django schema migration, to create all the tables needed to run the app.
    - Creates a Django superuser (you can also skip this and run `./manage.py createsuperuser` later).
      
    If you re-run `./setup_dev.sh` it will create any missing setup, but won't stomp on existing setup.  
    So if you do want to nuke the DB and start over, run `./nuke_db.sh`.
    

Starting a Dev Server
---------------------

Run `./run_dev_server.sh`.  This will start up a local postgres database server on port 5432, 
and a Django server serving the DICPick app at [http://localhost:8000/].  

If you `ctrl-c` out of this, both servers will shut down.
Obviously, you can't run two instances of this script on the same machine at once, due to port collisions.

Note that in some corner cases, when the Django server is particularly wedged due to a bug, you may not get a clean 
shutdown of the postgres server, in which case you may have to kill the `psql` processes manually. 


Initial Data
------------

Naturally, the running instance is only useful if you put some data into it.
You have three options for getting data into the DB:

* Create it all manually.  This will require logging in to the Django admin site ([http://localhost:8000/admin/]()) 
  as the superuser.  In the admin you'll need to:
    - Create a Camp object, and two user Group objects (one for camp admins and one for camp members).  
    - Create a User object that is a member of both those groups.
  
  Now you can log in to the DICPick UI at [http://localhost:8000/]() as that admin user.
  (Confusingly, "admin user" here means "allowed to access the DICPick UI", and has nothing to do with 
  Django superusers or the Django admin site).

* Run `./manage.py setup_dev_data`, which will create some fake data useful for playing around and testing.

* Import a data dump from a production instance of DICPick.  Our current production instance is deployed on Heroku,
  so the following steps assume you have the Heroku toolbelt installed, and have access permissions to the DICPick
  deployment.
    - Run `heroku pg:backups capture` to capture a backup.  This can take a few seconds.
    - Run `./dump_production_database.sh` to fetch that backup to `./latest.dump` on your local disk.
      You can re-run this, and it will fetch the last captured backup.
    - Run `./nuke_db.sh` to clean up any old database state, and then re-run `./setup_dev.sh`.  That
      script will notice the `./latest.dump` file and offer to import it.  Note that this imports
      all user auth information, including (salted and encrypted) passwords, so use with care!


Grokking the Code
-----------------

Again, we assume experience with Django.  The main app is under `django/` and its models, views and forms are 
well-documented.  Note in particular the various performance hacks to prevent floods of database queries
for ManyToManyFields in forms in a formset.

Things to note:

* `wsgi.py`, `settings.py` and the root `urls.py` live under `main/`, not under the root directory,
  as may be more typical in more simple Django apps. This is the author's personal preference. 
  See `./manage.py` and `Procfile` for how the dev and production environments, respectively, know about `/main`.
  
* A common problem in Django is how to maintain separate settings for dev vs. prod environments, and
  how to handle secrets that shouldn't be checked in anywhere. DICPick solves this thus:
    - `settings.py` contains the settings shared between dev and prod environments.
    - It also looks for an environment variable named `DICPICK_ENV`. If that variable has the value
      `dicpick_prod`, `settings.py` imports all the settings found in `settings_prod.py`. If that variable
      has the value `dicpick_dev`, or is unset, `settings.py` imports all the settings found in `settings_dev.py`.
    - `settings_dev.py` reads secret settings (such as the Django SECRET_KEY and the database password) from
      `settings_local.py`, which was generated by `./setup_dev.sh` and is gitignored and not checked in to the repo.
    - `settings_prod.py` reads secret settings from the Heroku environment.


Code Style
----------

We basically follow pep8, except with 2-space indents and 120 character lines.

### File Boilerplate

Every file (apart from `__init__.py` files, all of which must be empty - see below) must have the following header:

```
# coding=utf-8
# Copyright 2016 Mystopia.

from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)
```

(With the copyright year adjusted appropriately).


### Import Sorting

Run `./isort.sh` before committing, to ensure correct ordering of imports.


### `__init__.py`

`__init__.py` files should never contain code. They should be empty, and exist merely to mark packages.


### Tests

Unfortunately we don't currently have any tests.  TODO: Write some.


I18N
----
We use Django's i18n facilities to support the DIC terminology for Mystopia while allowing other camps to 
use more vanilla terms.  Basically, we support regular English via `en`, and a language variant `en_MYSTOPIA`.
The normal Django localization flow is used:
* Run `./makemessages.sh` to create the `.po` files in `dicpick/locale`.
* Edit the translations in the `.po` files.
* run `./compilemessages.sh` to create the `.mo` files.

Those scripts handle the trickiness of `gettext`'s assumptions about the cwd.

There is hardcoded logic in a view base class to check if the current camp is Mystopia, and set the user's
language preference appropriately.  In the future, if we want to allow other camps to have their own terminology,
or if we want to support other real languages, we'll need a more generic mechanism for matching users to languages.


Select2 and Autocomplete
------------------------
We enhance our select boxes using the excellent [select2](https://select2.github.io/) library.
This provides us with two important benefits:

- A Facebook-style multi-select widget.
- Autocompletion of options from a remote data source.

Why does this matter?
The DICPick UI contains a lot of multiple-select boxes, for tags and for participants. And these are
replicated across all forms in a formset.

For example, each participant has a "do not assign with" widget, where you can select other 
participants not to be assigned to the same task as this one. With 100 participants, that's 
100 select boxes on the page. And using a standard &lt;select&gt; each one
would have 100 &lt;option&gt; elements leading to 10,000 &lt;option&gt; elements on the page. This is
slow both on the server (when rendering the page) and on the client (when rendering it).

This is why autocomplete is so beneficial: The only &lt;option&gt; elements on the page are those
of the actually selected options.

There is a downside: select2 initialization is slow, and since we can have a few hundred of
these widgets on a page, it can take a couple of seconds for the page to initialize after
it loads. There may be some improvements we can make, but this would require performance
profiling.


Deploying DICPick
-----------------

This assumes you have Heroku toolbelt set up, and access permissions to the DICPick deployment.

Simply run `./deploy.sh`, which will walk you through all the steps.
See [materiality.util.deploy](https://github.com/benjyw/materiality.commons/blob/master/src/python/materiality/util/deploy.py) 
in `materiality.commons` for details on the deploy steps.

In particular, see [materiality.django.static](https://github.com/benjyw/materiality.commons/tree/master/src/python/materiality/django/static)
in `materiality.commons` for details on how static assets are gathered.

The DICPick production site uses SendGrid for sending password reset emails, and New Relic for monitoring.

The Initial Deploy
------------------

The initial deploy required creating various config variables: 

| Variable name        | Value
|----------------------|---------------------
|DATABASE_URL          | &lt;provided by Heroku&gt;
|DICPICK_ENV           | dicpick_prod
|NEWRELIC_API_KEY      | &lt;provided by New Relic&gt;
|NEW_RELIC_APP_NAME    | &lt;provided by New Relic&gt;
|NEW_RELIC_LICENSE_KEY | &lt;provided by New Relic&gt;
|NEW_RELIC_LOG         | stdout
|SECRET_KEY            | &lt;django secret key, generated at initial deploy&gt;
|SENDGRID_PASSWORD     | &lt;provided by SendGrid&gt;
|SENDGRID_USERNAME     | &lt;provided by SendGrid&gt;
|WEB_CONCURRENCY       | 2

These don't need changing when redeploying, but the information is preserved here for posterity.

Debugging in Production
-----------------------

If you want to temporarily turn debug mode on in production, set TEMPORARY_PROD_DEBUG_MODE_REMOVE_ME:

`heroku config:set TEMPORARY_PROD_DEBUG_MODE_REMOVE_ME=1`

But remember to unset it as soon as you've debugged whatever problem you've encountered:

`heroku config:unset TEMPORARY_PROD_DEBUG_MODE_REMOVE_ME`

