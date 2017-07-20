'use strict'

const _ = require('lodash')
const url = require('url')
const path = require('path')
const debug = require('debug')('knexsql')
const Queue = require('sync-queue')

function parseKnexConnection (uri) {
  if (!uri) {
    return undefined
  }
  if (uri.startsWith('sqlite://')) {
    return {filename: uri.slice(9)}
  }
  const parsed = url.parse(uri)
  const auth = parsed.auth ? parsed.auth.split(':') : []
    debug(auth)
  var returnMe = {
    host: parsed.hostname,
    port: parsed.port,
    user: auth[0] || process.env.KNEXSQL_USER,
    password: auth[1] || process.env.KNEXSQL_PASSWORD
  }
    if (parsed.pathname) {
	returnMe.database = parsed.pathname.slice(1)
    }
    return returnMe
}

function parseDatabaseType (uri) {
  return uri.split(':')[0]
}

function getKnexConfig (uri) {
  const knexConfig = {
    sqlite: {client: 'sqlite3'},
    mysql: {client: 'mysql'},
    mssql: {client: 'mssql'},
    postgres: {client: 'pg', pool: {min: 1, max: 1}},
    oracle: {
      client: 'strong-oracle',
      useNullAsDefault: true,
      pool: {min: 0, max: 7}
    }
  }
  const databaseType = parseDatabaseType(uri)
  if (!knexConfig[databaseType]) {
    throw new Error('Invalid database type in DB URI "' + uri + '"')
  }
  const migrations = {directory: path.join(__dirname, 'migrations')}
  const connection = parseKnexConnection(uri)
    debug(connection)
  const commonConfig = {connection, migrations}
  var returnMe = _.assign(commonConfig, knexConfig[databaseType])
    debug(returnMe)
  return _.assign(commonConfig, knexConfig[databaseType])
}


function processInput(knex, cb) {
    var buffer = ""
    var lineReader = require('readline').createInterface(process.stdin, process.stdout)
    var pending = 0;

    var closeFunc = function(err) {
	if (err == false && pending > 0) {
	    // Wait for any pending sql to return.
	    //debug("closeFunc waiting. " + pending)
	    //process.nextTick(function(){closeFunc(err)}) <-- does not work.
	    setTimeout(function() {closeFunc(err)}, 100)
	} else {
	    if (buffer.trim() != "") {
		console.error("Buffer not empty!  Did you forget semicolon?")
	        console.error(buffer)
                process.exit(1)
	    }
	    // Newline to clear prompt.
	    console.log("\n")

	    cb(err)
	}
    }

    // TODO Make prompt specific to the database name.
    lineReader.setPrompt('knexsql> ')
    lineReader.prompt()

    // Use sync-queue to ensure we execute SQL in the order it appeared.
    var queue = new Queue();
    lineReader.on('line', function(line) {
	debug("Got: " + line)

	if (line == 'quit') {
	    debug("quitting.")
	    buffer = ""
	    return closeFunc(false)
	}

        // If at the end of a SQL command, execute it.
        var semicolon = line.endsWith(";")

        // However, "$$" starts (and ends) escapes in postgres.  So don't execute if we are in the middle of one.
        var escape = line.startsWith("$$") || (buffer.indexOf("$$") != -1)
        // If we've started, and ended the escape, we can ignore the escape.
        if (escape) {
            var pattern = new RegExp("\\$\\$", "g")
            var count = buffer.match(pattern).length
            if (count % 2 == 0) {
                escape = false
            }
        }

        // Append the line to our buffer.  We can ignore empty lines, and comment lines.
        if (escape || (line.trim() != "" && !line.startsWith("--"))) {
            buffer = buffer + "\n" + line;
        }

	if (semicolon && !escape) {
            // We've detected end of SQL statement, execute it.
	    var sql = buffer
	    buffer = ""
	    pending++;
            queue.place(function() {
	        debug("executing:")
	        debug(sql)
	        knex.raw(sql)
	            .then(function(result) {
		        debug("result:")
		        debug(result)
		        pending--;
                        queue.next();
	                lineReader.prompt()
	            })
	            .catch(function(err) {
		        debug("error:")
		        console.error(err)
		        pending--;
                        queue.next();
		        lineReader.prompt()
	            })
            })
	}
    })

    lineReader.on('close', function() {
	debug("close event.")
	closeFunc(false)
    })
}

try {
    const uri = process.env.KNEXSQL_DB;
    if (!uri) {
	throw new Error('Must set environment variable KNEXSQL_DB')
    }

    const knex = require('knex')(getKnexConfig(uri))

    // Unclear whether there is any clean way to know whether knex has connected.
    knex.raw('SELECT 42').then(function () {
	console.log("here.  connected.")

	// Node's promises my head spin way too much to use a transaction here.
	//return knex.transaction(function(trx) {
	//    processInput(knex, trx)
	//})

	processInput(knex, function(err) {
	    // knex.close() Apparently not a thing!
	    if (err) {
		console.error(err)
		process.exit(1)
	    }
	    else {
		process.exit(0)
	    }
	})

    }).catch(function(e) {
	console.error(e)
	process.exit(2)
    })

}
catch (e) {
    console.error(e)
    process.exit(3)
}
