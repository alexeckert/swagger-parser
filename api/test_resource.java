/*api
* @Path("/order")
* @Api(value = "/order", description = "Some ordering stuff", produces = "application/json, application/xml")
*/
public class OrderResource {
  static OrderData petData = new OrderData();

  /*api
  * @Path("/{orderId}")
  * @ApiOperation(httpMethod = "GET", value = "Find order by ID",
  *   notes = "get an order given it's ID...",
  *   response = "Pet"
  * )
  * @ApiResponses(value = { @ApiResponse(code = 400, message = "Invalid ID supplied"),
  *     @ApiResponse(code = 404, message = "Order not found") })
  * @ApiImplicitParams(value = {
  *   @ApiImplicitParam(name = "orderId", value = "ID of order that needs to be fetched", allowableValues = "range[1, 5]", required = true, dataType = "Long", paramType = "path")
  * })
  */
  public Response getOrderById(Long petId) {
    Order pet = petData.getPetbyId(petId);
    if (null != pet) {
      return Response.ok().entity(pet).build();
    }
  }

}
