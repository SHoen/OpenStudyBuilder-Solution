
function prepareParameters (options, filters, sort, filtersUpdated) {
  const params = {
    pageNumber: (options.page),
    pageSize: options.itemsPerPage,
    totalCount: true
  }
  if (filtersUpdated) {
    /* Filters changed, reset page number */
    options.page = 1
  }
  if (filters !== undefined && filters !== '{}') {
    params.filters = filters
  }
  if (options.sortBy && options.sortBy.length !== 0 && sort !== undefined) {
    params.sortBy = `{"${options.sortBy[0]}":${!sort}}`
  }
  return params
}

export default {
  prepareParameters
}
