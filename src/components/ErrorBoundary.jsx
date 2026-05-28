import { Component } from "react";

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="error-box" style={{ margin: "2rem" }}>
          <strong>Something went wrong</strong>
          <p style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>{this.state.error.message}</p>
          <button className="btn btn-sm" style={{ marginTop: "1rem" }} onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
