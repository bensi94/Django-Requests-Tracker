# Example Project

This example project demonstrates the usage of Django Requests Tracker.
The project has a simple example API both for Django Ninja and Django REST Framework.


### Getting Started (locally)
* Install requirements:
  ```console
  pip install -r requirements.txt
  ```
* Migrate the database:
    ```console
    python manage.py migrate
    ```
* Create demo data:
    ```console
    python manage.py create_demo_data
    ```
* Run the development server:
    ```console
    python manage.py runserver
    ```
* Go to [http://localhost:8000/__requests_tracker__/](http://localhost:8000/__requests_tracker__/) to see the running Requests Tracker,
the requests list will however be empty as there are no requests yet.


* Run example requests with management command.
    ```console
    python manage.py run_example_requests
    ```

### Using the API manually

#### Django Ninja part
* Go to [http://localhost:8000/ninja/docs](http://localhost:8000/ninja/docs)
to explore and execute requests to the Django Ninja part.

#### Django REST Framework part
* Go to [http://localhost:8000/restframework/docs](http://localhost:8000/restframework/docs)
to explore available endpoints in the Django REST framework part.
Use Postman or similar clients to execute requests.
