/*api
* @GET
* @Path("/{petId}")
* @ApiOperation(value = "Find pet by ID",
*   notes = "Returns a pet when ID < 10.  ID > 10 or nonintegers will simulate API error conditions",
*   response = Pet.class,
*   authorizations = @Authorization(value = "api_key")
* )
* @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid ID supplied"),
*     @ApiResponse(code = 404, message = "Pet not found") })
* @ApiParam(value = "ID of pet that needs to be fetched", allowableValues = "range[1,5]", required = true) @PathParam("petId") Long
*/
public Response getPetById(Long petId)
    throws com.github.kongchen.swagger.sample.wordnik.exception.NotFoundException {
  Pet pet = petData.getPetbyId(petId);
  if (null != pet) {
    return Response.ok().entity(pet).build();
  } else {
    throw new com.github.kongchen.swagger.sample.wordnik.exception.NotFoundException(404, "Pet not found");
  }
}
