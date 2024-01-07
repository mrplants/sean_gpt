import React from 'react';

const About = () => {
    return (
        <div className="container mx-auto p-4">
            <div className="card  bg-base-100 shadow-md">
                <div className="card-body text-center items-center">
                  <div className="flex w-full">
                    <div className="flex-1 flex justify-end">
                      <h2 className="card-title lg:text-2xl">AI</h2>
                    </div>
                    <div className="divider divider-horizontal">over</div>
                    <div className="flex-1 flex justify-start">
                      <h2 className="card-title lg:text-2xl">SMS</h2>
                    </div>
                  </div>
                  <div className="lg:flex">
                    <div className="lg:flex-1">
                      <h3 className="font-bold">Inclusion</h3>
                      <p className='my-2'>
                        Text with your AI assistant- SeanGPT is AI over SMS.
                      </p>
                      <p className='my-2'>
                          Because it works over SMS, SeanGPT does not require any app downloads or internet connectivity. It's designed to work with the most basic mobile phones, ensuring that anyone can have access to cutting edge AI assistance no matter who or where you are.
                      </p>
                    </div>
                    <div className="divider lg:divider-horizontal"></div>
                    <div className="lg:flex-1">
                      <h3 className="font-bold">Security</h3>
                      <p className='my-2'>
                        We don't train AI models on your messages.
                      </p>
                      <p className='my-2'>
                        You are the only human that will see your data.  An AI model will look at your data, but only in response to your request.  Afterward, it forgets everything it has seen. SeanGPT makes it impossible for your data to leak into another user's messages.
                      </p>
                    </div>
                  </div>
                </div>
            </div>
        </div>
    );
};

export default About;

{/* <div className="divider"></div> 
<div>
</div>
<div className="divider divider-horizontal"></div>
<div>
</div>
<div className="divider"></div> 
<h3 className="">Access to AI is a human right, finally.</h3> */}
