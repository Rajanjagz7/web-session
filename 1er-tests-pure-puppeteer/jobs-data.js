// 15 distinct NSW jobs spanning both activity types, both building types,
// a spread of lead-generation methods (values confirmed live against the
// dev site's current dropdown - the old "Phone/Email/Website/Referral"
// labels no longer exist there), and a spread of Sydney-metro suburbs.
// Dates are deliberately unique/ascending so they never collide.
module.exports = [
  { customerName: 'Olivia Bennett', addressSearch: '1 George Street Sydney', postcode: '2000', activityType: 'Heating & Cooling', buildingType: 'Residential Building', leadMethod: 'Customer initiated contact', installationDate: '28-08-2026' },
  { customerName: 'Jack Sullivan', addressSearch: '50 Elizabeth Street Artarmon', postcode: '2064', activityType: 'Hot Water Heat Pump', buildingType: 'Residential Building', newSystem: 'Heat pump', leadMethod: 'Online advertisement', installationDate: '29-08-2026' },
  { customerName: 'Mia Robertson', addressSearch: '123 Walker Street North Sydney', postcode: '2060', activityType: 'Heating & Cooling', buildingType: 'Small Business Site', leadMethod: 'Social media', installationDate: '01-09-2026' },
  { customerName: 'Noah Fitzgerald', addressSearch: '66 Pacific Highway St Leonards', postcode: '2065', activityType: 'Hot Water Heat Pump', buildingType: 'Small Business Site', leadMethod: 'Email campaign', installationDate: '02-09-2026' },
  { customerName: 'Ava Thompson', addressSearch: '789 New Canterbury Road Dulwich Hill', postcode: '2203', activityType: 'Heating & Cooling', buildingType: 'Residential Building', leadMethod: 'Print advertisement', installationDate: '03-09-2026' },
  { customerName: 'Lucas Whitfield', addressSearch: '898 Punchbowl Road Punchbowl', postcode: '2196', activityType: 'Hot Water Heat Pump', buildingType: 'Residential Building', newSystem: 'Heat pump', leadMethod: 'Pamphlet', installationDate: '04-09-2026' },
  { customerName: 'Charlotte Nguyen', addressSearch: '15 Spring Street Bondi Junction', postcode: '2022', activityType: 'Heating & Cooling', buildingType: 'Residential Building', leadMethod: 'Promotional booth', installationDate: '05-09-2026' },
  { customerName: 'Ethan Walker', addressSearch: '200 Victoria Avenue Chatswood', postcode: '2067', activityType: 'Hot Water Heat Pump', buildingType: 'Residential Building', newSystem: 'Solar (electric boosted)', leadMethod: 'TV advertisement', installationDate: '06-09-2026' },
  { customerName: 'Isla Campbell', addressSearch: '45 Church Street Parramatta', postcode: '2150', activityType: 'Heating & Cooling', buildingType: 'Small Business Site', leadMethod: 'Radio advertisement', installationDate: '07-09-2026' },
  { customerName: 'Henry Martin', addressSearch: '12 King Street Newtown', postcode: '2042', activityType: 'Hot Water Heat Pump', buildingType: 'Small Business Site', leadMethod: 'Other', installationDate: '08-09-2026' },
  { customerName: 'Grace Turner', addressSearch: '88 Beach Road Bondi Beach', postcode: '2026', activityType: 'Heating & Cooling', buildingType: 'Residential Building', leadMethod: 'Customer initiated contact', installationDate: '09-09-2026' },
  { customerName: 'Oliver Reid', addressSearch: '300 George Street Liverpool', postcode: '2170', activityType: 'Hot Water Heat Pump', buildingType: 'Residential Building', newSystem: 'Heat pump', leadMethod: 'Email campaign', installationDate: '10-09-2026' },
  { customerName: 'Amelia Foster', addressSearch: '10 Sydney Road Manly', postcode: '2095', activityType: 'Heating & Cooling', buildingType: 'Residential Building', leadMethod: 'Online advertisement', installationDate: '11-09-2026' },
  { customerName: 'William Hayes', addressSearch: '25 Kingsway Cronulla', postcode: '2230', activityType: 'Hot Water Heat Pump', buildingType: 'Residential Building', newSystem: 'Solar (electric boosted)', leadMethod: 'Social media', installationDate: '12-09-2026' },
  { customerName: 'Sophia Clarke', addressSearch: '200 Peats Ferry Road Hornsby', postcode: '2077', activityType: 'Heating & Cooling', buildingType: 'Small Business Site', leadMethod: 'Print advertisement', installationDate: '13-09-2026' },
];
