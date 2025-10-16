# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

#imports
import sys
import logging
import warnings

#specific imports
from typing import Any

#application imports
from .arguments.arguments import ToolingArguments
from .commands.factory import CommandFactory, Question, QuestionSQL
from .utils.term_menu import clear_cli_terminal

# Suppress future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class App:
    """Main application class for AWS Cost Optimization Workshop tool"""
    def __init__(self, mode='cli'):
        self.logger = logging.getLogger(__name__)
        self.mode = mode
        
        self._setup_application() #parse arguments; initialize database

    def _setup_application(self) -> None:
        #setup config
        from .config.config import Config 
        self.appConfig = Config()
        '''
        Setup default path locations; report time; 
        create database path locations; defaults; create tables
        download pricing information
        Set config values and set internal parameters 
        '''
        self.appConfig.setup(self.mode)

        #parse_arguments
        raw_arguments = sys.argv[1:]
        self.logger.info(f'Starting CostMinimizer with parameters : {raw_arguments}')
        self.appConfig.arguments_parsed = ToolingArguments().command_line_arguments(raw_arguments)
        
        #setup auth manager and authentication
        #TODO this should not be handled inside config
        '''
        Determine if we are inside a ec2 instance, ecs container or local workstation and determine permissions
        Determine intended region to select
        Create boto sessions
        '''
        self.appConfig.setup_authentication()
        
        '''
        Setup automatic configuration of tool and database
        Write reports to databasde
        '''
        self.appConfig.database_initial_defaults()

    def _handle_standard_mode(self, cmd: Any) -> Any:
        result = cmd.run()
        return result if self.appConfig.mode == 'module' else None

    def main(self) -> Any:
        """Main execution method"""
        try:
            clear_cli_terminal(self.appConfig.mode)

            self.logger.info(f'################################## Starting CostMinimizer tool in {self.appConfig.mode} mode ##################################')

            #exit if application has not been configured
            if not self.appConfig.validate_database_configuration():
                self.appConfig.handle_missing_configuration()
                return

            #obtain command object
            cmd = CommandFactory().create(arguments=self.appConfig.arguments_parsed, app=self)

            if isinstance(cmd, Question) or isinstance(cmd, QuestionSQL):
                cmd.validate_genai_request()
                return cmd.execute()
            else:
                return self._handle_standard_mode(cmd)
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            print(f"An unexpected error occurred. Please check the logs for more information: {str(e)}.")
            # print(f"Error: {e}")
            self.appConfig.console.print(f'\n[red]\n{e}[/red]')
            return None
        
def main():
    """
    Main entry point for the application.
    """
    app = App()
    return app.main()

if __name__ == "__main__":
    main()
