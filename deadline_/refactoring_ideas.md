Here we keep ideas about refactoring the overall code

1. Since all endpoints contain a test for not working without authentication (setting the HTTP_AUTHORIZATION header),
    introduce some structure which automatically creates such tests