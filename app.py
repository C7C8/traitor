#!/usr/bin/env python3

#  This file is part of traitor.
#
#  traitor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  traitor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with traitor.  If not, see <https://www.gnu.org/licenses/>.
#

from aws_cdk import core

from cdk.cdk_stack import CdkStack

app = core.App()
CdkStack(app, "traitor")
app.synth()
