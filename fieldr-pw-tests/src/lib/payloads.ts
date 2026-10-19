/**
 * PLACEHOLDER payload field names for the API seeding fixture.
 * TODO(confirm): none of these keys has been checked against the real API. Change a value here and every seed follows;
 * nothing else in the suite hard-codes a request body key.
 */
export const KEY = {
  customer: {
    company: 'companyName', // TODO(confirm)
    contactName: 'contactName', // TODO(confirm)
    email: 'email', // TODO(confirm)
    mobile: 'mobile', // TODO(confirm)
    isActive: 'isActive', // TODO(confirm)
  },
  quote: {
    customerId: 'customerId', // TODO(confirm)
    title: 'title', // TODO(confirm)
    lines: 'lines', // TODO(confirm)
    lineName: 'name', // TODO(confirm)
    lineQty: 'quantity', // TODO(confirm)
    lineSell: 'sellPrice', // TODO(confirm)
    lineCost: 'costPrice', // TODO(confirm)
  },
  job: {
    customerId: 'customerId', // TODO(confirm)
    name: 'name', // TODO(confirm)
    description: 'description', // TODO(confirm)
    quoteId: 'quoteId', // TODO(confirm)
  },
  invite: {
    email: 'email', // TODO(confirm)
    kind: 'type', // TODO(confirm): staff or customer
    link: 'inviteUrl', // TODO(confirm): response field that holds the accept link
  },
  user: {
    firstName: 'firstName', // TODO(confirm)
    lastName: 'lastName', // TODO(confirm)
    email: 'email', // TODO(confirm)
    mobile: 'mobile', // TODO(confirm)
  },
  role: {
    name: 'name', // TODO(confirm)
  },
} as const;
