

set jg_server ""
set jg_server_semaphore ""

set jg_server_debug 1

proc debug_puts {msg} {
    global jg_server_debug
    if {$jg_server_debug eq 1} {
        puts $msg
    }
}

proc handle_client {sock addr port} {

    global jg_server
    global jg_server_semaphore

    puts "Accepted connection from [fconfigure $sock -peername] on port $port"

    global env; puts $env(PATH)

    fconfigure $sock -buffering line -encoding utf-8

    while {[gets $sock action] != -1} {

        puts "Received action: $action"

        if {$action eq "CLOSE"} {
            # Close current connection
            close $sock
            puts "Connection closed."
            return
        } elseif {$action eq "SHUTDOWN"} {
            # Close the current connection and server
            close $sock
            puts "Connection closed."
            jg_stop_server
            return
        } elseif {$action eq "EVAL"} {

            puts "Getting command."

            if {[gets $sock command] != -1} {

                puts "Received command: $command"

                set error [catch {eval $command} result]

                puts "Result: $result"
                puts "Error: $error"

                if {$error == 0} {
                    # Send non-error return code
                    set errorstr "0"

                } else {
                    # Send error code
                    set errorstr "1"
                }

                set reslen [string length $result]
                set lenstr [format "%08x" $reslen]

                puts "Sending result length: $lenstr"
                puts "Sending result: $result"

                puts $sock $errorstr$lenstr$result
            } else {
                puts "Error reading command."
            }
        }

    }

    close $sock
    puts "Connection closed."

}

proc jg_start_server {port} {
    global jg_server
    global jg_server_semaphore

    # Create a server socket
    set jg_server [socket -server handle_client $port]
    puts "Server started on port $port"

    # fconfigure $server_socket -blocking 1  ;# Set the socket to blocking mode

    # Wait for the server to be closed
    vwait jg_server_semaphore
    close $jg_server
    puts "Server closed."
}

proc jg_stop_server {} {
    global jg_server_semaphore

    puts "Setting semaphore."
    set jg_server_semaphore "closed"
}
