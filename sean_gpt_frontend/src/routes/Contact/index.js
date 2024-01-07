import { useCallback, useEffect, useState } from 'react';
import { GoogleReCaptchaProvider, useGoogleReCaptcha } from 'react-google-recaptcha-v3';
import toast from 'react-hot-toast';

const ContactForm = () => {
  const { executeRecaptcha } = useGoogleReCaptcha();
  const [recaptchaToken, setRecaptchaToken] = useState(null);

  const handleReCaptchaVerify = useCallback(async () => {
    if (!executeRecaptcha) {
      return;
    }

    try {
      const token = await executeRecaptcha('contact_form');
      setRecaptchaToken(token);
    } catch (error) {
      console.error('ReCaptcha Error:', error);
    }
  }, [executeRecaptcha]);

  // Automatically trigger reCAPTCHA verification when the component loads
  useEffect(() => {
    handleReCaptchaVerify();
  }, [handleReCaptchaVerify]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await handleReCaptchaVerify();
    // TODO: Submit form to backend
    toast.success('Message sent!');
    // Reset the form fields
    console.log('recaptchaToken', recaptchaToken);
    e.target.reset();
  };

  return (
    <form onSubmit={handleSubmit} className="form-control">
      <h2 className="card-title lg:text-2xl">Get in Touch</h2>
      <p className="my-2">
        Have questions or want to learn more about SeanGPT? Reach out to us.
      </p>
      <div className="form-control">
        <label className="label">
          <span className="label-text">Your Name</span>
        </label>
        <input type="text" placeholder="Name" className="input input-bordered" required/>
      </div>
      <div className="form-control">
        <label className="label">
          <span className="label-text">Your Email</span>
        </label>
        <input type="email" placeholder="Email" className="input input-bordered" required/>
      </div>
      <div className="form-control">
        <label className="label">
          <span className="label-text">Message</span>
        </label>
        <textarea className="textarea textarea-bordered" placeholder="Your message" required></textarea>
      </div>
      <div className="form-control my-6">
        <button type='submit' className="btn btn-primary" >Send Message</button>
      </div>
      <p className="text-sm text-center my-2">
        This site is protected by reCAPTCHA and the Google <a href="https://policies.google.com/privacy" className='link'>Privacy Policy</a> and <a href="https://policies.google.com/terms"className='link'>Terms of Service</a> apply.
      </p>
    </form>
  );
};

const Contact = () => {
  return (
    <div className="container mx-auto p-4">
      <div className="card bg-base-100 shadow-md">
        <div className="card-body text-center">
          <GoogleReCaptchaProvider reCaptchaKey="6LesFkkpAAAAANpMd_mNeFtFpAZxRdeJVRgi4_P2">
            <ContactForm />
          </GoogleReCaptchaProvider>
        </div>
      </div>
    </div>
  );
};

export default Contact;
