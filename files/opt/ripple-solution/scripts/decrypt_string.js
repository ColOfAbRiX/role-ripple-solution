// ©Copyright 2016-2017 Ripple Labs Inc., All Rights Reserved.
// Ripple Labs, Inc. Proprietary and Confidential
// Unauthorized copying and distribution strictly prohibited
'use strict'
const {decryptString} = require('shared')

const publicKey = process.argv[2]
let plaintext = ''
process.stdin.on('data', function(chunk) {
  plaintext += chunk
})
process.stdin.on('end', function() {
  decryptString(plaintext.trim(), publicKey).then(encryptedString => {
    console.log(encryptedString)
  }).catch(err => {
    console.error(err.message)
    process.exit(1)
  })
})
