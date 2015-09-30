# Inline Annotation Guidelines

### Annotation format:

All annotations must adhere to the following format:

```
/*api
* ...
* @ApiOperation(...)
* ...
*/
```

Some things to note:

- There should be no spaces between `/*api`
- Each new line should start with the `*` character, followed by a space and then the tag.
- End the API annotation with `*/` on a separate line

## @Api
This annotation is required in all the files that you want parsed as resources/controllers.

### Format:

Both the *value* and *description* parameters <u>must</u> be specified in the @Api tag.

```
@Api(value="onlinestore", description="Operations pertaining to Online Store")
```

Format of @Api should always have value and description specified

## @GET/POST/PUT/DELETE

An HTTP method <u>must</u> be specified for any Java method documented in the API. **The HTTP method must be the first tag specified in the list of annotations as shown below**:

```
/*api
* @GET
* ...
*/
```
