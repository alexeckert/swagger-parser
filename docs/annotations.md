### Annotation format:

All annotations must adhere to the following format:

```
/*api
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

Without any parameters:

```
@Api()
```

Or with a value specified
```
@Api(value = "/pet")
```

Tag order:

```
@Api(value = "/pet")
```
