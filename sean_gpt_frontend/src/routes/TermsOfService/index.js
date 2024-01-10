import React from 'react';
import { Link } from 'react-router-dom';

const TermsOfService = () => {
    return (
    <div className="container mx-auto p-4">
      <div className="card-body  items-center">
        <h2 className="card-title text-lg lg:text-2xl">Terms of Service</h2>
        <div className="prose">
            <p>Welcome to SeanGPT! By accessing or using our AI chat service over SMS, the web, or any other medium, you agree to be bound by these terms of service.</p>
            
            <ol>
                <li>
                    <h3>Acceptance of Terms</h3>
                    <p>By accessing and using SeanGPT, you accept and agree to be bound by the terms and provision of this agreement.</p>
                </li>

                <li>
                    <h3>Modification of Terms</h3>
                    <p>We reserve the right to modify these terms at any time. Your continued use of SeanGPT after any such changes constitutes your acceptance of the new terms.</p>
                </li>

                <li>
                    <h3>Privacy Policy</h3>
                    <p>Our Privacy Policy explains how we treat your personal data and protect your privacy when you use our Service. By using our Service, you agree that SeanGPT can use such data in accordance with our privacy policies.</p>
                </li>

                <li>
                    <h3>Service Usage by Minors</h3>
                    <p>SeanGPT is not intended for and may not be used by individuals under the age of 18. By using SeanGPT, you represent that you are at least 18. Minors must not access or use the service.</p>
                </li>

                <li>
                    <h3>User Responsibilities</h3>
                    <p>Users are responsible for their conduct and their data. Use of SeanGPT for any illegal or unauthorized purpose is prohibited.</p>
                </li>

                <li>
                    <h3>Service Availability</h3>
                    <p>We strive to ensure the availability of the service at all times, but we do not guarantee uninterrupted or error-free operation.</p>
                </li>

                {/* <li>
                    <h3>Intellectual Property</h3>
                    <p>All rights, title, and interest in and to SeanGPT are and will remain the exclusive property of [Your Company Name].</p>
                </li> */}

                <li>
                    <h3>Disclaimer of Warranties</h3>
                    <p>The service is provided "as is". We make no warranties regarding the reliability, accuracy, or performance of the service.</p>
                </li>

                <li>
                    <h3>Limitation of Liability</h3>
                    <p>We shall not be liable for any indirect, incidental, special, consequential or punitive damages, including loss of profits, data, or use.</p>
                </li>

                <li>
                    <h3>Governing Law</h3>
                    <p>These terms shall be governed by the laws of the jurisdiction of California, without regard to its conflict of law provisions.</p>
                </li>

                <li>
                    <h3>Contact Information</h3>
                    <p>If you have any questions about these Terms, please <Link className='link' to='/contact'>contact us</Link>.</p>
                </li>
            </ol>
            <p>Last updated: 7 January 2024</p>
        </div>
      </div>
    </div>
    )
};

export default TermsOfService;