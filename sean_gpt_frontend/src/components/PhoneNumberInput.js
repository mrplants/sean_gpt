import React from 'react';
import InputMask from 'react-input-mask';

function PhoneNumberInput({ className, value, setValue, ...props }) {
  const handleChange = (e) => {
    // Clean up the input value so that it only contains digits and the plus sig
    const cleanValue = e.target.value.replace(/[^+\d]/g, '');
    setValue(cleanValue);
  };
  
  return (
    <InputMask mask="+1 (999) 999-9999" placeholder="+1 (___) ___-____" value={value} onChange={handleChange} {...props}>
      {(inputProps) => <input {...inputProps} className={className} type="tel" />}
    </InputMask>
  );
}

export default PhoneNumberInput;