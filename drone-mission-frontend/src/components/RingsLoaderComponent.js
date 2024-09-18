import React from 'react';
import { Rings } from 'react-loader-spinner';

const RingsLoaderComponent = () => {
  return (
    <Rings
      visible={true}
      height="80"
      width="80"
      color="#4fa94d"
      ariaLabel="rings-loading"
      wrapperStyle={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}
      wrapperClass=""
    />
  );
};

export default RingsLoaderComponent;