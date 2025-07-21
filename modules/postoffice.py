import json, requests


class Discord_message:

    def __init__( self, content : str = None, files : list = None, username = None, avatar_url = None, embeds = None ):
        self.content    = content,
        self.files      = files
        self.username   = username
        self.avatar_url = avatar_url
        self.embeds     = embeds

        # TODO: Validate
        self.message = {
            "content"    : content,
            "username"   : username,
            "avatar_url" : avatar_url,
            "embeds"     : embeds,
        }

        self.response = None


    def send( self, webhook_urls : list ):
        for url in webhook_urls:

            # Skip other webhooks
            if "discord.com".lower() not in url.lower():
                continue

            # Sending files
            if self.files != None:
                self.response = requests.post(
                    url,
                    files = self.files
                )

                return self.handle_response()
            
            # No files, send prepared message. 
            self.response = requests.post(
                url,
                json    = self.message
            )
            
            return self.handle_response()


    def handle_response( self ):
        return True


class Slack_message:

    def __init__( self, text : str ):
        self.text = text

        self.response = None

    def send( self, webhook_urls : list ):
        for url in webhook_urls:
    
            if "hooks.slack.com".lower() not in url.lower():
                continue

            self.response = requests.post(
                url,
                data    = json.dumps({ "text" : self.text }),
                headers = { "Content-Type" : "application/json" }
            )
            
            print(self.response)
            return self.handle_response()


    def handle_response( self ):
        # TODO:
        return True


def send( 
          webhook_urls : list[str], 
          discord_message : Discord_message = None, slack_message : Slack_message = None ) -> bool:
    
    #
    #   Validate the parameters
    #

    # No message objects
    if (discord_message == None) and (slack_message == None):
        raise(TypeError(
            "Both parameters 'discord_message' and 'slack_message' can't be 'None'! Please provide either or both with an appropriate object.")
        ) 
        return False

    # No webhooks
    if (webhook_urls == []):
        raise (TypeError( "Parameter 'webhook_urls' must be provided with an list that is not empty." ))
        return False

    #
    #   Send webrequests to webhooks
    #

    slack_success   = None
    discord_success = None
    
    if slack_message:
        slack_success   = slack_message.send( webhook_urls )

    if discord_message:
        discord_success = discord_message.send( webhook_urls )

    
    # Check for fails
    if (not slack_success   and slack_success   != None) or \
       (not discord_success and discord_success != None):
        return False
    
    return True
