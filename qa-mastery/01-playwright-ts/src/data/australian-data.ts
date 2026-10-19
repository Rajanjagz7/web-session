/**
 * Curated, verified Australian test data library for RebateM8 NSW E2E Testing
 */

export interface AuAddress {
  street: string;
  suburb: string;
  state: string;
  postcode: string;
}

export interface ResidentialCustomer {
  fullName: string;
  phone: string;
  email: string;
  address: AuAddress;
}

export interface BusinessCustomer {
  businessName: string;
  abn: string;
  signatoryFirstName: string;
  signatoryLastName: string;
  signatoryPosition: string;
  phone: string;
  email: string;
  address: AuAddress;
}

export const AU_TEST_DATA = {
  installerCompany: 'Rajan Testing Company',
  installerPerson: 'Rajan Jagwani',

  residentialCustomers: [
    {
      fullName: 'Olivia Nguyen',
      phone: '+61412345678',
      email: `olivia.nguyen.${Date.now()}@yopmail.com`,
      address: {
        street: '12 Macquarie St',
        suburb: 'Sydney',
        state: 'NSW',
        postcode: '2000'
      }
    },
    {
      fullName: 'Jack Wilson',
      phone: '+61423456789',
      email: `jack.wilson.${Date.now()}@yopmail.com`,
      address: {
        street: '88 George St',
        suburb: 'The Rocks',
        state: 'NSW',
        postcode: '2000'
      }
    },
    {
      fullName: 'Mia Collins',
      phone: '+61434567890',
      email: `mia.collins.${Date.now()}@yopmail.com`,
      address: {
        street: '45 Hunter St',
        suburb: 'Newcastle',
        state: 'NSW',
        postcode: '2300'
      }
    }
  ],

  businessCustomers: [
    {
      businessName: 'Apex Innovations NSW Pty Ltd',
      abn: '33102417032', // Valid 11-digit Australian ABN
      signatoryFirstName: 'Aria',
      signatoryLastName: 'Patel',
      signatoryPosition: 'Managing Director',
      phone: '+61458901234',
      email: `aria.patel.biz.${Date.now()}@yopmail.com`,
      address: {
        street: '15 Crown St',
        suburb: 'Wollongong',
        state: 'NSW',
        postcode: '2500'
      }
    },
    {
      businessName: 'Pacific Rim Logistics Pty Ltd',
      abn: '51824753556', // Valid 11-digit Australian ABN
      signatoryFirstName: 'Noah',
      signatoryLastName: 'Smith',
      signatoryPosition: 'Operations Director',
      phone: '+61467890123',
      email: `noah.smith.logistics.${Date.now()}@yopmail.com`,
      address: {
        street: '10 Church St',
        suburb: 'Parramatta',
        state: 'NSW',
        postcode: '2150'
      }
    }
  ],

  activityTypes: {
    heatingCooling: 'Heating & Cooling',
    hotWaterHeatPump: 'Hot Water Heat Pump'
  },

  buildingTypes: {
    residential: 'Residential Building',
    smallBusinessSmall: 'Small Business Site (less than 273 kWh/day)',
    smallBusinessLarge: 'Small Business Site (273 kWh/day or more)'
  },

  leadGenerationMethods: [
    'Customer initiated contact',
    'Online advertisement',
    'Social media',
    'Email campaign'
  ]
};
