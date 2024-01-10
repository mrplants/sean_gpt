import React from 'react';

const FAQ = () => {
    return (
        <div className="container m-auto p-4">
            <h2 className="text-center text-lg lg:text-2xl mb-4">Frequently Asked Questions</h2>
            <div className="accordion" id="faqAccordion">
            <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        When will SeanGPT be available over SMS?
                    </div>
                    <div className="collapse-content"> 
                        <p>We have submitted our approval request for an <a href="https://www.twilio.com/docs/messaging/compliance/a2p-10dlc" className='link'>A2P 10DLC campaign</a> to our messaging service provider and expect to hear back any day now- stay tuned!  In the meantime, feel free to use SeanGPT over the web.</p>
                    </div>
                </div>
                <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        How does SeanGPT work over SMS?
                    </div>
                    <div className="collapse-content"> 
                        <p>SeanGPT proxies your SMS requests to private endpoints of the world's most advanced AI models. This means you can interact with it just like texting a friend, without needing any internet connection or app downloads.</p>
                    </div>
                </div>
                <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        Do I need a laptop or smartphone to use SeanGPT?
                    </div>
                    <div className="collapse-content"> 
                        <p>No, an expensive device is not necessary. SeanGPT is designed to work with any mobile phone that can send and receive SMS, ensuring accessibility for all users.</p>
                    </div>
                </div>
                <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        How is my privacy protected?
                    </div>
                    <div className="collapse-content"> 
                        <p>We store your message history and use it as context for your future requests. Our databases use industry standard security protections.</p>
                    </div>
                </div>
                <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        Is there a cost associated with using SeanGPT?
                    </div>
                    <div className="collapse-content"> 
                        <p>Standard SMS charges by your mobile carrier may apply when you send and receive messages.</p>
                    </div>
                </div>
                <div className="collapse collapse-arrow bg-base-200 my-2">
                    <input type="radio" name="faq" />
                    <div className="collapse-title text-md lg:text-xl font-medium">
                        Can SeanGPT understand messages in different languages?
                    </div>
                    <div className="collapse-content"> 
                        <p>Yes! Today's AI models are incredibly powerful- try your native language and see how it responds!</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FAQ;
