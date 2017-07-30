# Gift Registry Apps

- gifts: Implement Gift Registry

Simple migration is needed from v1 to v2 since make_many_bought_by_list is called on migration to v2
to populate bought_by_list. bought_by can be deprecated once refactored out completely.



## Install Required Packages

To install it use the following command:

    pip install -r requirements.txt


## Running the Application

Before running the application we need to create the needed DB tables:

    ./manage.py migrate

Now you can run the development web server:

    ./manage.py runserver

To access the applications go to the URL <http://localhost:8000/>

    ./manage.py createsuperuser

To create a normal user (non super user), you must login to the admin page and
create it: <http://localhost:8000/admin/>
