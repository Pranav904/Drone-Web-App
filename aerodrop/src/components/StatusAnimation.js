import React from "react";
import { motion } from "framer-motion";
import { CheckCircleIcon, XCircleIcon } from "@heroicons/react/24/solid";
import RingsLoaderComponent from "./RingsLoaderComponent";
import "./StatusAnimation.css";

const StatusAnimation = ({ status, message }) => {
  if (status === "loading") {
    return <RingsLoaderComponent />;
  }

  if (status === "success" || status === "error") {
    const Icon = status === "success" ? CheckCircleIcon : XCircleIcon;
    const colorClass = status === "success" ? "text-green-500" : "text-red-500";

    return (
      <div className="animation">
        <motion.div
          className={`${status}-animation`}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          transition={{ duration: 0.5, exit: { duration: 0.5, delay: 2 } }}
        >
          <Icon className={colorClass} />
          <p className="msg">{status === "success" ? "Success!" : "Error!"}</p>
          <p className="msg">{message}</p>
        </motion.div>
      </div>
    );
  }

  return null;
};

export default StatusAnimation;
