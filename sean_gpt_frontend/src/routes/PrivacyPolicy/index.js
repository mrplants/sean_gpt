import React from 'react';
import { Link } from 'react-router-dom';

const PrivacyPolicy = () => {
    return (
        <div className="container mx-auto p-4">
            <div className="card-body items-center">
                <h2 className="card-title text-lg lg:text-2xl">Privacy Policy</h2>
                <div className="prose">
                    <p>This Privacy Policy outlines how SeanGPT handles your personal information and data. We respect your privacy and are committed to protecting it through our compliance with this policy.</p>

                    <ol>
                        <li>
                            <h3>Information Collection and Use</h3>
                            <p>We collect several types of information from and about users of our Service, including information by which you may be personally identified, such as telephone number.</p>
                        </li>

                        <li>
                            <h3>Data Security</h3>
                            <p>We have implemented measures designed to secure your personal information from accidental loss and from unauthorized access, use, alteration, and disclosure.</p>
                        </li>

                        <li>
                            <h3>Information Sharing</h3>
                            <p>We do not share your personal information with any third parties except as described in this Privacy Policy.</p>
                        </li>

                        <li>
                            <h3>Your Rights and Choices</h3>
                            <p>You have the right to access, correct, or delete your personal information. You can also object to the processing of your personal information, request the restriction of processing of your personal information or request portability of your personal information.</p>
                        </li>

                        <li>
                            <h3>Children's Privacy</h3>
                            <p>Our Service does not address anyone under the age of 18. We do not knowingly collect personally identifiable information from children under 18.</p>
                        </li>

                        <li>
                            <h3>Changes to Our Privacy Policy</h3>
                            <p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.</p>
                        </li>

                        <li>
                            <h3>Contact Information</h3>
                            <p>If you have any questions about this Privacy Policy, please <Link className='link' to='/contact'>contact us</Link>.</p>
                        </li>
                    </ol>
                    <p>Last updated: 7 January 2024</p>
                </div>
            </div>
        </div>
    )
};

export default PrivacyPolicy;
