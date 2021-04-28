from aws_cdk import core, aws_lambda as lambda_, aws_apigateway as apigw



class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hello_lambda = lambda_.Function(self, "HelloHandler",
                                        runtime=lambda_.Runtime.PYTHON_3_8,
                                        code=lambda_.Code.asset('lmbda'),
                                        handler="hello.handler")
        apigw.LambdaRestApi(self, 'test', handler=hello_lambda)
